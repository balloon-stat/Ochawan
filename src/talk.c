#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <memory.h>
#include <sys/types.h>
#include <sys/stat.h>
#include "SDL.h"
#include "SDL_audio.h"
#include "AquesTalk2.h"
#include "talk.h"

extern void toHira(char* str);

/* WAVE ファイルの情報を格納する構造体 */
typedef struct {
	FILE* fp;        /* ファイル構造体 */
	short is_pcm;    /* PCM フォーマットの場合は 1、それ以外は 0 */
	short channel;   /* モノラルの場合は 1、ステレオの場合は 2 */
	int   rate;      /* サンプリング周波数 */
	short bits;      /* 量子化ビット数 */
	long  offset;    /* ファイル先頭から PCM データまでのオフセット */
	int   len;       /* PCM データ部の長さ */
} WAVE;

#define NUM_SOUNDS 2
struct sample {
    Uint8 *data;
    Uint32 dpos;
    Uint32 dlen;
} sounds[NUM_SOUNDS];

/* 関数プロトタイプ */
int  wave_read( char* wav, WAVE* fmt );
void mixaudio(void *unused, Uint8 *stream, int len);
void PlaySound(char* wav, WAVE* fmt);
void set_SDL(void);
void openAudio_SDL(int samples);
void* file_load(const char* file, int* size);
void WavVolume(unsigned char *wav, int Volume);


int phont_size = 0;
void* pPhont = NULL;

void open(void) {
    set_SDL();
    openAudio_SDL(0);
    SDL_PauseAudio(0);
    pPhont = file_load("aq.phont", &phont_size);
    if (pPhont == 0)
        printf("Can not read aq.phont");
}

void close(void) {
    SDL_CloseAudio();
    SDL_Quit();
    free(pPhont);
}

int talk(char *s) {
    int iret;
    char str[1024];
    unsigned char *wav;
    WAVE fmt;

    strcpy(str, s);
    printf("str:%s\n", str);
    toHira(str);
    printf("str:%s\n", str);
    wav = AquesTalk2_Synthe_Utf8(str, 85, &phont_size, pPhont);
    if (wav == 0) {
        fprintf(stderr, "ERR:%d\n",phont_size);
        return 0;
    }

    wave_read((char*)wav, &fmt);
    WavVolume(wav, 20);
    PlaySound((char*)wav, &fmt);

    AquesTalk2_FreeWave(wav);
    return 1;
}

void set_SDL(void) {
    if (SDL_Init(SDL_INIT_AUDIO) < 0) {
        fprintf(stderr, "Unable to init SDL: %s\n", SDL_GetError());
        exit(1);
    }
}

void openAudio_SDL(int samples) {
    SDL_AudioSpec sfmt;

    sfmt.freq= 44100; /* Sampling rate: 8kHz */
    sfmt.format= AUDIO_S16LSB; /* 16-bit signed audio */
    sfmt.channels= 2; /* Mono */
    sfmt.samples= samples; // * 44100 / 8000; /* Buffer size */
    sfmt.callback= mixaudio;
    sfmt.userdata= NULL;

    if (SDL_OpenAudio(&sfmt, NULL) < 0 ) {
        fprintf(stderr, "Unable to open audio: %s\n", SDL_GetError());
        exit(1);
    }
}
/*
 * WAVE ファイル情報を読み込む
 */
int wave_read( char* wav, WAVE* fmt )
{
	int len, pointer;

	/* 
	 * 先頭 4 バイトが "RIFF" であることを確認
	 */

	if ( strncmp( wav, "RIFF", 4 ) != 0 ) {
		fprintf( stderr, "Specified file is not RIFF file.\n" );
		return -1;
	}


	/* "WAVE" であることを確認 */

	if ( strncmp( wav + 8, "WAVE", 4 ) != 0 ) {
		fprintf( stderr, "Specified file is not WAVE file.\n" );
		return -1;
	}

	pointer = 20;

	/* fmt チャンクを探す */
	len = *( int* )( &wav[16] );
	pointer += len;

	if ( strncmp( wav + 12, "fmt ", 4 ) != 0 ) {
		fprintf( stderr, "Failed to find fmt chunk.\n" );
		return -1;
	}


	/* WAVE フォーマットを読み込む */

	fmt->is_pcm  = *( ( short* )( &wav[20]  ) );
	fmt->channel = *( ( short* )( &wav[22]  ) );
	fmt->rate    = *( ( int*   )( &wav[24]  ) );
	fmt->bits    = *( ( short* )( &wav[34]  ) );

	if ( fmt->is_pcm != 1 ) {
		fmt->is_pcm = 0;
	}

	/* data チャンクを探す */
	len = *( int* )( &wav[pointer + 4] );

	if ( strncmp( wav + pointer, "data", 4 ) != 0 ) {
		fprintf( stderr, "Failed to find data chunk.\n" );
		return -1;
	}

	fmt->len = len;
	fmt->offset = pointer + 8;
	printf( "\n" );
	//printf( "WAVE file format :\n" );
	//printf( " rate    = %d\n",  fmt->rate );
	//printf( " channel = %d\n",  fmt->channel );
	//printf( " bits    = %d\n",  fmt->bits );
	//printf( " offsets = %ld\n", fmt->offset );
	printf( " length  = %d\n",  fmt->len );
	printf( "\n" );

	return 0;
}

void mixaudio(void *unused, Uint8 *stream, int len)
{
    int i;
    Uint32 amount;

    for ( i=0; i<NUM_SOUNDS; ++i ) {
        amount = (sounds[i].dlen-sounds[i].dpos);
        if ( amount > len ) {
            amount = len;
        }
        SDL_MixAudio(stream, &sounds[i].data[sounds[i].dpos], amount, SDL_MIX_MAXVOLUME);
        sounds[i].dpos += amount;
    }
}

void PlaySound(char* wav, WAVE *fmt)
{
    int index;
    SDL_AudioCVT cvt;

    /* 空の(あるいは終了した)サウンドスロットを探す */
    for ( index=0; index<NUM_SOUNDS; ++index ) {
        if ( sounds[index].dpos == sounds[index].dlen ) {
            break;
        }
    }
    if ( index == NUM_SOUNDS )
        return;

    /* サウンドファイルをロードして 22kHz 16bit ステレオに変換する */
    SDL_BuildAudioCVT(&cvt, AUDIO_S16LSB, 1, 8000,
                            AUDIO_S16LSB, 2, 44100);
    cvt.buf = malloc(fmt->len * cvt.len_mult);
    memcpy(cvt.buf, wav + fmt->offset, fmt->len);
    cvt.len = fmt->len;
    SDL_ConvertAudio(&cvt);

    /* サウンドデータをスロットに置く(すぐに再生を始めます) */
    if ( sounds[index].data ) {
        free(sounds[index].data);
    }
    SDL_LockAudio();
    sounds[index].data = cvt.buf;
    sounds[index].dlen = cvt.len_cvt;
    sounds[index].dpos = 0;
    SDL_UnlockAudio();
}

void* file_load(const char* file, int* size) {
    FILE* fp;
    char* data;
    struct stat st;

    *size = 0;

    if (stat(file, &st) != 0)
        return NULL;

    if ((data = (char*)malloc(st.st_size)) == NULL) {
        fprintf(stderr, "Can not alloc memory(file_load)\n");
        return NULL;
    }
    if ((fp = fopen(file, "rb")) == NULL) {
        free(data);
        perror(file);
        return NULL;
    }
    if (fread(data, 1, st.st_size, fp) < (unsigned)st.st_size) {
        fprintf(stderr, "Can not read data(file_load)\n");
        free(data);
        fclose(fp);
        return NULL;
    }
    fclose(fp);
    *size = st.st_size;
    return data;
}

void WavVolume(unsigned char *wav, int Volume) {

    unsigned long len = (*(unsigned long*)(wav+40))/2;

    short *swave = (short*)(wav+44);

    for(unsigned long i=0; i<len; i++){

        int val = swave[i]*Volume/100;

        if(val>32767)       swave[i] =  32767;

        else if(val<-32768) swave[i] = -32768;

        else                swave[i] = (short)val;

    }
}
