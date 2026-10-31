uint8_t r5_crc4(uint32_t w){
 uint8_t c=15;w&=0xfffffff0u;
 for(int b=31;b>=0;b--){unsigned f=((c>>3)^((w>>b)&1u))&1u;c=(c<<1)&15u;if(f)c^=3u;}
 return c;
}
bool r5_tm_crc_ok(uint32_t w){return w!=0&&w!=UINT32_MAX&&r5_crc4(w)==(w&15u);}
uint16_t r5_tm_data(uint32_t w){return (uint16_t)(w>>8);}
bool r5_tm_valid(const uint32_t *t){
 for(unsigned j=0;j<8;j++)if(!r5_tm_crc_ok(t[j])||(t[j]&0xc0000080u))return false;
 uint16_t pre=r5_tm_data(t[3]),post=r5_tm_data(t[4]);
 if((pre&0x2700)!=0x2700||(post&0x2700)!=0x2700||((pre^post)&0x70))return false;
 if(r5_tm_data(t[5])&0x9f03)return false;
 if(r5_tm_data(t[6])&0x783f)return false;
 if(r5_tm_data(t[7])!=0x3130)return false;
 for(unsigned j=0;j<3;j++){int v=(int16_t)r5_tm_data(t[j]);if(v>31129||v< -31129)return false;}
 return true;
}
