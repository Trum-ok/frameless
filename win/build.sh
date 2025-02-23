#!/bin/bash

GOOS=windows GOARCH=amd64 CGO_ENABLED=1 CC="gcc" go build -ldflags="-s -w" -o server.exe server-win.go