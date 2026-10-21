#include "static_gateway.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static unsigned reads;
static uint16_t read_fake(void* context,unsigned port){(void)context;++reads;return (uint16_t)(100+port);}
int main(int argc,char** argv)
{
    const unsigned counts[6]={3,6,9,9,7,7};
    pd5_usb frame={0},decoded={0};frame.type=PD5_SCAN;frame.device=123;frame.boot=456;frame.capture[0]=1;frame.scan=1;frame.request_us=1000;frame.start_us=2000;pd5_blank_scan(&frame);
    for(unsigned n=1;n<=6;n++){
        pd5_region_request req={(uint8_t)n,PD5_REQUEST,456,1000+n,n},parsed;
        pd5_region_result result={0},parsed_result;result.node=(uint8_t)n;result.count=(uint8_t)counts[n-1];result.gateway_boot=456;result.boot=1000+n;result.token=n;result.duration_us=500;
        uint8_t query[28],response[52],fragment[8];pd5_fragments rx={0};
        pd5_acquire_ports(&result,counts[n-1],read_fake,NULL);
        assert(pd5_encode_request(&req,query));
        for(unsigned f=0;f<4;f++){pd5_make_fragment(query,28,f,fragment);assert(pd5_fragment(&rx,fragment,28,2000+f)==(f==3?1:0));}
        assert(pd5_decode_request(rx.data,28,&parsed)&&parsed.expected_boot==req.expected_boot);
        assert(pd5_encode_result(&result,response));rx=(pd5_fragments){0};
        for(unsigned f=0;f<8;f++){pd5_make_fragment(response,52,f,fragment);assert(pd5_fragment(&rx,fragment,52,2000+f)==(f==7?1:0));}
        assert(pd5_decode_result(rx.data,52,&parsed_result));
        parsed_result.token++;assert(!pd5_merge_region(&frame,&parsed_result,&req,3000+n*1000));parsed_result.token--;
        parsed_result.boot++;assert(!pd5_merge_region(&frame,&parsed_result,&req,3000+n*1000));parsed_result.boot--;
        assert(pd5_merge_region(&frame,&parsed_result,&req,3000+n*1000));
        assert(!pd5_merge_region(&frame,&parsed_result,&req,3000+n*1000));
        for(unsigned i=0;i<52;i++){response[i]^=1;assert(!pd5_decode_result(response,52,&parsed_result));response[i]^=1;}
        rx=(pd5_fragments){0};pd5_make_fragment(query,28,1,fragment);assert(pd5_fragment(&rx,fragment,28,10)==-1);
        pd5_make_fragment(query,28,0,fragment);assert(!pd5_fragment(&rx,fragment,28,10));pd5_make_fragment(query,28,1,fragment);assert(pd5_fragment(&rx,fragment,28,100011)==-1);
    }
    assert(reads==41&&frame.physical_mask==PD5_FULL_MASK);
    uint8_t usb[220];assert(pd5_encode_usb(&frame,usb));assert(pd5_decode_usb(usb,220,&decoded));assert(decoded.physical_mask==PD5_FULL_MASK);
    for(unsigned i=0;i<220;i++){usb[i]^=1;assert(!pd5_decode_usb(usb,220,&decoded));usb[i]^=1;}
    for(unsigned n=0;n<220;n++)assert(!pd5_decode_usb(usb,n,&decoded));
    if(argc==2){FILE* f=NULL;assert(!fopen_s(&f,argv[1],"wb")&&f);assert(fwrite(usb,1,220,f)==220);fclose(f);}
    pd5_blank_scan(&frame);assert(frame.physical_mask==0&&frame.words[3]==PD5_MISSING&&frame.words[0]==PD5_FIXED);
    pd5_region_result single={0};single.node=3;single.count=9;pd5_acquire_ports(&single,1,read_fake,NULL);assert(single.mask==1&&single.words[1]==PD5_MISSING&&reads==42);
    puts("PASS PDG5/PDC5 host tests: 41 fresh callbacks, partial bench, CAN fragment/order/deadline, token/boot/replay, 532 CRC mutations, USB truncation, blank cohorts; no hardware");return 0;
}
