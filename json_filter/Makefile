# VoiceHealth JSON validator — requires cJSON.c and cJSON.h in this directory.
# Get them from: https://github.com/DaveGamble/cJSON

CC     = gcc
CFLAGS = -Wall -Wextra -I.
SRC    = validate_voicehealth_json.c
CJSON  = cJSON.c
OBJ    = validate_voicehealth_json.o cJSON.o

# Default: build the CLI + test executable
all: validate_cli validate_test

# Static library for linking into other projects
libvalidate.a: $(OBJ)
	ar rcs $@ validate_voicehealth_json.o cJSON.o

validate_voicehealth_json.o: validate_voicehealth_json.c validate_voicehealth_json.h cJSON.h
	$(CC) $(CFLAGS) -c validate_voicehealth_json.c -o $@

cJSON.o: cJSON.c cJSON.h
	$(CC) $(CFLAGS) -c cJSON.c -o $@

# Test program
validate_test: validate_voicehealth_json.o cJSON.o test_validate.c
	$(CC) $(CFLAGS) -o $@ test_validate.c validate_voicehealth_json.o cJSON.o

# CLI wrapper for Python subprocess usage (reads JSON from stdin)
validate_cli: validate_voicehealth_json.o cJSON.o validate_cli.c validate_voicehealth_json.h
	$(CC) $(CFLAGS) -o $@ validate_cli.c validate_voicehealth_json.o cJSON.o

clean:
	rm -f $(OBJ) libvalidate.a validate_test validate_cli

.PHONY: all clean
