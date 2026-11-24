
int main() {
    unsigned int i = 1;
    unsigned int a,b,c,d;
    a = i + 2;
    b = a * 2;
    c = b << 2;
    d = a + b + c + i;

    if (d == 34) {
        return 1;
    }
    else {
        return 0;
    }
}