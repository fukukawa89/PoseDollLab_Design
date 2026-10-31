#include "raw46.h"
#include <stdio.h>
#include <assert.h>
#include <string.h>
static uint16_t response(uint16_t v){unsigned n=0;for(unsigned i=0;i<15;i++)n^=(v>>i)&1u;return (uint16_t)(v|(n<<15));}
int main(int argc,char**argv){
 p17_message m={0},r;uint8_t bytes[192],bad[192];m.type=P17_SCAN;m.device=0x010203040506;m.transport_boot=7;m.body_boot=9;m.scan=1;m.token=2;m.request_us=100;m.start_us=101;m.end_us=45001;m.valid_mask=P17_MASK;
 for(unsigned i=0;i<16;i++)m.capture[i]=(uint8_t)(i+1);
 for(unsigned i=0;i<46;i++)m.words[i]=(uint16_t)(37*i);
 assert(p17_encode(&m,bytes));assert(p17_decode(bytes,192,&r));assert(r.words[45]==1665);
 for(unsigned bit=0;bit<192*8;bit++){memcpy(bad,bytes,192);bad[bit/8]^=(uint8_t)(1u<<(bit%8));assert(!p17_decode(bad,192,&r));}
 for(size_t n=0;n<192;n++)assert(!p17_decode(bytes,n,&r));
 unsigned flips=0;
 for(unsigned count=1;count<=10;count++){
  uint16_t rx[6][10]={0},out[10];
  for(unsigned i=0;i<count;i++){rx[1][i]=response(0x100);rx[2][i]=response(1234);rx[3][i]=response((uint16_t)(1000+i));}
  assert(p17_decode_chain(rx,count,out));for(unsigned i=0;i<count;i++)assert(out[i]==1000+count-1-i);
  for(unsigned burst=1;burst<6;burst++)for(unsigned word=0;word<count;word++)for(unsigned bit=0;bit<16;bit++){
   rx[burst][word]^=(uint16_t)(1u<<bit);assert(!p17_decode_chain(rx,count,out));assert(out[count-1-word]&P17_FAULT);rx[burst][word]^=(uint16_t)(1u<<bit);flips++;
  }
  memset(rx,0,sizeof(rx));assert(!p17_decode_chain(rx,count,out));memset(rx,255,sizeof(rx));assert(!p17_decode_chain(rx,count,out));
 }
 assert(p17_command(0x3fff)==0xffff);assert(p17_command(0x3ffd)==0x7ffd);
 if(argc==2){FILE*f=NULL;assert(fopen_s(&f,argv[1],"wb")==0);assert(fwrite(bytes,1,192,f)==192);fclose(f);}
 printf("P17 native PASS: 1536 packet bit flips, 192 truncations, %u sensor response bit flips, 10 chain lengths\n",flips);return 0;
}
