
int ZenString_index_of(ZenString s, ZenString sub) {
    if (!s || !sub) return -1;
    char* pos = strstr(s, sub);
    if (!pos) return -1;
    return (int)(pos - s);
}
