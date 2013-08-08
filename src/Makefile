OBJ=talk.o toHiragana.o
PROG=libtalk.so
GCC=gcc
#LIBS= -Ilib64 -Llib64 -lAquesTalk2Eva -lasound -lanthy -lanthydic

LIBS= -I/usr/include/SDL -Ilib64 -Llib64 -lAquesTalk2Eva -D_GNU_SOURCE=1 -D_REENTRANT -L/usr/lib/x86_64-linux-gnu -lSDL -lanthy -lanthydic


.PHONY : all
all: $(PROG)

$(PROG): $(OBJ)
	$(GCC) -shared -o $@ $(OBJ) $(LIBS)

.c.o:
	$(GCC) -fPIC -std=gnu99 -c $< $(LIBS)

.PHONY : run
run:
	./$(PROG)
