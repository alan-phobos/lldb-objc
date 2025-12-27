# Makefile for HelloWorld example
# This simple Objective-C program is used for testing LLDB commands

TARGET = HelloWorld/HelloWorld
SOURCE = HelloWorld/main.m

# Compiler and flags
CC = clang
CFLAGS = -framework Foundation -g -fobjc-arc

# Build the binary
$(TARGET): $(SOURCE)
	$(CC) $(CFLAGS) -o $(TARGET) $(SOURCE)

# Clean build artifacts
clean:
	rm -f $(TARGET)

# Rebuild from scratch
rebuild: clean $(TARGET)

# Run the binary
run: $(TARGET)
	./$(TARGET)

.PHONY: clean rebuild run
