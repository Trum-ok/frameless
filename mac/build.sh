#!/bin/bash

GOOS=darwin GOARCH=arm64 CGO_ENABLED=1 CC="clang -arch arm64" go build -ldflags="-s -w" -o server server-mac.go
