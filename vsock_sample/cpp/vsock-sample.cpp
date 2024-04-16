#include <iostream>
#include <chrono>
#include <vector>
#include <algorithm>
#include <cstring>
#include <sys/types.h>
#include <sys/socket.h>
#include <linux/vm_sockets.h>
#include <unistd.h>
#include <cassert>
#include <numeric>

class VsockStream {
private:
    int conn_tmo;
    int sock;
    std::vector<double> records;

public:
    VsockStream(int conn_tmo = 5) : conn_tmo(conn_tmo) {}

    void _connect(struct sockaddr_vm* endpoint) {
        sock = socket(AF_VSOCK, SOCK_STREAM, 0);
        if (sock == -1) {
            perror("socket");
            exit(EXIT_FAILURE);
        }

        if (connect(sock, (struct sockaddr*)endpoint, sizeof(struct sockaddr_vm)) == -1) {
            perror("connect");
            exit(EXIT_FAILURE);
        }
    }

    void send_data(const void* data, size_t size) {
        if (send(sock, data, size, 0) == -1) {
            perror("send");
            exit(EXIT_FAILURE);
        }
        recv_data();
    }

    void recv_data() {
        uint8_t buffer[8];
        ssize_t bytes_received = recv(sock, buffer, sizeof(buffer), 0);
        if (bytes_received == -1) {
            perror("recv");
            exit(EXIT_FAILURE);
        }
        auto curr = std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
        auto recv_time = *reinterpret_cast<uint64_t*>(buffer);
        auto delta = curr - recv_time;
        records.push_back(delta / 1000.0);
    }

    void disconnect() {
        close(sock);
        assert(records.size() % 2);
        std::sort(records.begin(), records.end());
        std::cout << "For " << records.size() << " samples, median = " << records[records.size() / 2] << "\u00B5s" << std::endl;
        double mean = std::accumulate(records.begin(), records.end(), 0.0) / records.size();
        double res = std::accumulate(records.begin(), records.end(), 0.0, [mean](double acc, double val) {
            return acc + (val - mean) * (val - mean);
        }) / records.size();
        std::cout << "90th: " << records[static_cast<size_t>(0.9 * records.size())] << std::endl;
        std::cout << "95th: " << records[static_cast<size_t>(0.95 * records.size())] << std::endl;
        std::cout << "99th: " << records[static_cast<size_t>(0.99 * records.size())] << std::endl;
        std::cout << "Variance: " << res << std::endl;
    }
};

void client_handler(int cid, int port) {
    VsockStream client;
    struct sockaddr_vm endpoint = {
        .svm_family = AF_VSOCK,
        .svm_port = static_cast<unsigned int>(port),
        .svm_cid = static_cast<unsigned int>(cid)
    };
    client._connect(&endpoint);
    for (int i = 0; i < 50001; ++i) {
        uint64_t time_now = std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
        client.send_data(&time_now, sizeof(time_now));
    }
    client.disconnect();
}

class VsockListener {
private:
    int conn_backlog;
    int sock;

public:
    VsockListener(int conn_backlog = 128) : conn_backlog(conn_backlog) {}

    void _bind(int port) {
        std::cout << "here" << std::endl;
        sock = socket(AF_VSOCK, SOCK_STREAM, 0);
        if (sock == -1) {
            perror("socket");
            exit(EXIT_FAILURE);
        }

        struct sockaddr_vm local_endpoint = {
            .svm_family = AF_VSOCK,
            .svm_port = static_cast<unsigned int>(port),
            .svm_cid = VMADDR_CID_ANY,
        };
        if (bind(sock, (struct sockaddr*)&local_endpoint, sizeof(local_endpoint)) == -1) {
            perror("bind");
            exit(EXIT_FAILURE);
        }

        if (listen(sock, conn_backlog) == -1) {
            perror("listen");
            exit(EXIT_FAILURE);
        }
    }

    void recv_data() {
        struct sockaddr_vm client_endpoint;
        socklen_t client_endpoint_len = sizeof(client_endpoint);
        while (true) {
            int from_client = accept(sock, (struct sockaddr*)&client_endpoint, &client_endpoint_len);
            if (from_client == -1) {
                perror("accept");
                exit(EXIT_FAILURE);
            }
            char buffer[8];
            ssize_t bytes_received;
            while ((bytes_received = recv(from_client, buffer, sizeof(buffer), 0)) > 0) {
                if (send(from_client, buffer, bytes_received, 0) == -1) {
                    perror("send");
                    exit(EXIT_FAILURE);
                }
            }
            close(from_client);
        }
    }
};

void server_handler(int port) {
    VsockListener server;
    server._bind(port);
    server.recv_data();
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <client|server> [args]" << std::endl;
        return EXIT_FAILURE;
    }

    if (std::strcmp(argv[1], "client") == 0) {
        if (argc != 4) {
            std::cerr << "Usage: " << argv[0] << " client <cid> <port>" << std::endl;
            return EXIT_FAILURE;
        }
        client_handler(std::stoi(argv[2]), std::stoi(argv[3]));
    } else if (std::strcmp(argv[1], "server") == 0) {
        if (argc != 3) {
            std::cerr << "Usage: " << argv[0] << " server <port>" << std::endl;
            return EXIT_FAILURE;
        }
        server_handler(std::stoi(argv[2]));
    } else {
        std::cerr << "Unknown command: " << argv[1] << std::endl;
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
