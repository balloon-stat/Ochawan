#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <anthy/anthy.h>

#define BUFSIZE 1024

/* Array of skip-bytes-per-initial character. */
const char * const utf8_skip;
#define utf8_next_char(p) (char *)((p) + utf8_skip[*(unsigned char *)(p)])

static const char utf8_skip_data[256] = {
1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,
3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,4,4,4,4,4,4,4,4,5,5,5,5,6,6,1,1
};
const char * const utf8_skip = utf8_skip_data;


void toHira(char* str);
int istalk(unsigned char* word);
int isQues(unsigned char* str);
void replaceSign(unsigned char* str);
void replaceGrass(char* str);

void toHira(char* str) {
    int len, cur, isquestion;
    char buf[BUFSIZE];
    struct anthy_conv_stat cs;

    replaceSign(str);
    replaceGrass(str);
    printf("rgr_str:%s\n", str);
    isquestion = isQues(str);
    //printf("isques:%d\n", isquestion);

    if (anthy_init()) {
        fprintf(stderr, "anthy init error\n");
        abort();
    }

    anthy_context_t ctx = anthy_create_context();

    if (!ctx) {
        fprintf(stderr, "can not create context\n");
        abort();
    }

    anthy_context_set_encoding(ctx, ANTHY_UTF8_ENCODING);

    if (anthy_set_string(ctx, str)) {
        fprintf(stderr, "can not set string\n");
        abort();
    }

    if (anthy_get_stat(ctx, &cs)) {
        fprintf(stderr, "can not get stat\n");
        abort();
    }

    cur = 0;
    for (int i = 0; i < cs.nr_segment; i++) {
        if ((len = anthy_get_segment(ctx, i, NTH_UNCONVERTED_CANDIDATE,
                    buf, BUFSIZE)) == -1) {
            fprintf(stderr, "can not get segment %d\n", i);
            abort();
        }
        if (istalk(buf)) {
            memcpy(str + cur, buf, len);
            cur += len;
        }
        if (i < cs.nr_segment - 1)
            if (i == cs.nr_segment - 3 && isquestion)
                continue;
            else if (i == cs.nr_segment - 2)
                continue;
            else
                str[cur] = '/';
        else
            str[cur] = '\0';
        cur++;
    }

    anthy_release_context(ctx);
}

int istalk(unsigned char* word) {
    if (word[0] == '?' || word[0] == '/' || word[0] == 0x27 || word[0] == '+' ||
            word[0] == ',') // || word[0] == ';' ) // 0x27 = '
        return 1;
    else if (word[0] == 0xef && word[1] == 0xbc && word[2] == 0x9f) //「？」
        return 1;
    else if (word[0] != 0xe3)
        return 0;
    else if (word[1] == 0x80 && (word[2] == 0x81 || word[2] == 0x82)) // 、。
        return 1;
    else if (word[1] == 0x83 && word[2] == 0xbc) // ー
        return 1;
    else if (word[1] == 0x81 && word[2] > 0x80) // あ～
        return 1;
    else if (word[1] == 0x82 && word[2] < 0x94) // ～ん
        return 1;
    else
        return 0;
}

void replaceSign(unsigned char* str) {
    unsigned char* str_p = str;
    while(*str_p) {
        if (str_p[0] == 0xe3 && str_p[1] == 0x83 && str_p[2] == 0xbb) {
            str_p[1] = 0x80;
            str_p[2] = 0x81;
        } // ・ -> 、
        else if (str_p[0] == 0xe2 && str_p[1] == 0x80 && str_p[2] == 0x95) {
            str_p[0] = 0xe3;
            str_p[1] = 0x83;
            str_p[2] = 0xbc;
        } // ー(全角ハイフン) -> ー

        str_p = utf8_next_char(str_p);
    }
}

void replaceGrass(char* str) {
    char buf[BUFSIZE];
    char* str_p = buf;
    char* next = NULL;
    int len;

    strcpy(buf, str);
    while(*str_p) {
        next = utf8_next_char(str_p);
        len = next - str_p;

        if (*str_p == 'w') {
            memcpy(str, "わら", 6);
            str += 6;
        }
        else {
            memcpy(str, str_p, len);
            str += len;
        }

        str_p = next;
    }
    *str = '\0';
}

int isQues(unsigned char* str) {
    unsigned char * str_p;
    int ret;
    str_p = str;
    while(*str_p) {
        if (*str_p == '\n')
            break;
        if (*str_p == '?')
            ret = 1;
        else if (str_p[0] == 0xef && str_p[1] == 0xbc && str_p[2] == 0x9f) //「？」
            ret = 1;
        else
            ret = 0;

        str_p = utf8_next_char(str_p);
    }
    return ret;
}
