#include "remote_link.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char**argv){
 pdr4_message m={0},d={0};uint8_t bytes[PDR4_MAX_BYTES],mut[PDR4_MAX_BYTES];m.type=PDR4_REQUEST;m.link_nonce[0]=1;m.capture[0]=2;m.scan=1;m.generation=7;m.capture_counter=1;
 assert(pdr4_encode(&m,bytes,sizeof bytes)==68);assert(pdr4_decode(bytes,68,&d));assert(!pdr4_decode(bytes,67,&d));
 pdr4_session s;pdr4_reset(&s);assert(!pdr4_accept_request(&s,&m));assert(pdr4_bind(&s,m.link_nonce,7));assert(pdr4_accept_request(&s,&m));assert(!pdr4_accept_request(&s,&m));
 m.scan=2;assert(pdr4_accept_request(&s,&m));m.scan=1;m.capture_counter=2;m.capture[0]=3;assert(pdr4_accept_request(&s,&m));m.capture_counter=1;m.capture[0]=2;assert(!pdr4_accept_request(&s,&m));pdr4_reset(&s);assert(!pdr4_accept_request(&s,&m));m.type=PDR4_RESPONSE;m.duration_us=300000;m.words[0]=0;m.words[1]=0x8000;m.words[2]=0xc000;m.words[3]=16383;
 assert(pdr4_encode(&m,bytes,sizeof bytes)==80);assert(pdr4_decode(bytes,80,&d));assert(d.duration_us==300000&&d.words[1]==0x8000&&d.words[2]==0xc000);
 for(unsigned i=0;i<80;i++){memcpy(mut,bytes,80);mut[i]^=1;assert(!pdr4_decode(mut,80,&d));}
 if(argc>1){FILE*f=NULL;assert(fopen_s(&f,argv[1],"wb")==0);assert(fwrite(bytes,1,80,f)==80);fclose(f);}
 puts("PDR4 PASS: round-trip, lengths, CRC 80 corruptions, wide timing, faults preserved, reset/replay.");return 0;
}
