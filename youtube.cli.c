
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <video_id>\n", argv[0]);
        return 1;
    }

    char command[512];
    snprintf(command, sizeof(command), "sudo build/exe.macosx-10.13-universal2-3.12/video %s", argv[1]);

    return system(command);
}

