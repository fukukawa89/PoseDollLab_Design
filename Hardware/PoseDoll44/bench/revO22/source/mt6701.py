"""MT6701 24-bit SSI codec; mathematical tests do not certify physical wiring."""
def crc6(data):
    if type(data) is not int or not 0<=data<(1<<18):raise ValueError('18-bit payload')
    c=0
    for bit in range(17,-1,-1):
        feedback=(c>>5)^((data>>bit)&1);c=(c<<1)&63
        if feedback:c^=3
    return c
def decode_word(word,idle_high):
    if type(word) is not int or not 0<=word<=0xffffff:raise ValueError('SSI width')
    status=(word>>6)&15
    good=idle_high is True and status==0 and crc6(word>>6)==(word&63)
    return {'word':word,'counts':word>>10,'status':status,'crc_ok':crc6(word>>6)==(word&63),'idle_high':idle_high,'valid':good}
