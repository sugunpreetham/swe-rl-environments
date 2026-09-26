FROM gcc:13-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y cmake build-essential && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN cmake -B build && cmake --build build

CMD ["./build/spmv_verifier"]
