# VoiceHealth JSON validator — requires cJSON.c and cJSON.h in this directory.
# Get them from: https://github.com/DaveGamble/cJSON

CC     = gcc
CFLAGS = -Wall -Wextra -I.
SRC    = validate_voicehealth_json.c
CJSON  = cJSON.c
OBJ    = validate_voicehealth_json.o cJSON.o

# Default: build the test executable
all: validate_test

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

# Standalone validator (optional; add a main() in validate_voicehealth_json.c if needed)
# validate: $(OBJ) ...

clean:
	rm -f $(OBJ) libvalidate.a validate_test

.PHONY: all clean
