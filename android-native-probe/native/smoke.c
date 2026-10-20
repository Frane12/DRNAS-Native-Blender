#include <stdio.h>
#include <stdlib.h>
#include <sys/utsname.h>

int main(int argc, char **argv) {
    struct utsname info;
    if (uname(&info) != 0) {
        perror("uname");
        return 2;
    }
    puts("DRNAS NATIVE ARM64 EXECUTION: PASS");
    printf("Machine: %s\n", info.machine);
    printf("System: %s\n", info.sysname);
    printf("Argument: %s\n", argc > 1 ? argv[1] : "(none)");
    if (sizeof(void *) != 8) {
        fputs("Expected 64-bit pointers\n", stderr);
        return 3;
    }
    return 0;
}
