#include "raw46.h"
#include <assert.h>
#include <stdio.h>
/* Independent polynomial long division, not the streaming implementation. */
static uint8_t reference(uint32_t d){uint32_t x=d<<6;for(int i=23;i>=6;i--)if(x&(1u<<i))x^=0x43u<<(i-6);return (uint8_t)(x&63u);}
int main(void){
 for(uint32_t d=0;d<(1u<<18);d++)assert(p21_crc6(d)==reference(d));
 for(uint32_t a=0;a<16384;a++){
  uint32_t w=(a<<10)|reference(a<<4);
  assert(p21_sensor_valid(w,true));assert(!p21_sensor_valid(w,false));
  for(unsigned bit=0;bit<24;bit++)assert(!p21_sensor_valid(w^(1u<<bit),true));
  for(unsigned status=1;status<16;status++){uint32_t d=(a<<4)|status;assert(!p21_sensor_valid((d<<6)|reference(d),true));}
 }
 p21_message m={.type=P21_SCAN,.device=123,.transport_boot=456,.body_boot=456,.request_us=100,.start_us=101,.end_us=16000,.scan=1,.token=1,.valid_mask=P21_MASK,.idle_high_mask=P21_MASK},out;
 m.capture[0]=1;
 for(unsigned i=0;i<46;i++)m.words[i]=((i*307u)<<10)|reference(i*307u<<4);
 uint8_t bytes[P21_BYTES];assert(p21_encode(&m,bytes));assert(p21_decode(bytes,sizeof bytes,&out));assert(out.words[45]==m.words[45]);
 for(unsigned bit=0;bit<P21_BYTES*8;bit++){bytes[bit/8]^=(uint8_t)(1u<<(bit%8));assert(!p21_decode(bytes,sizeof bytes,&out));bytes[bit/8]^=(uint8_t)(1u<<(bit%8));}
 for(unsigned n=0;n<P21_BYTES;n++)assert(!p21_decode(bytes,n,&out));
 FILE*f=NULL;if(fopen_s(&f,"codec_fixture.bin","wb"))return 2;assert(fwrite(bytes,1,sizeof bytes,f)==sizeof bytes);fclose(f);
 m.valid_mask^=1;assert(!p21_encode(&m,bytes));
 m.valid_mask=P21_MASK;m.words[0]=0x1000000;assert(!p21_encode(&m,bytes));
 puts("P21 PASS: 262144 independent CRC comparisons; all 16384 angles, 393216 single-bit SSI corruptions, all 15 status codes, 1984 USB bit flips, truncations, masks.");
 return 0;
}
