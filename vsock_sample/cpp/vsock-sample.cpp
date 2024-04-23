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
#include <fstream>
#include <string>

const int EXPERIMENT_TIME = 10;  // MINUTES
const char* LOG_FILE = "records.csv";

void log_and_clear(std::vector<double>& records) {
    std::ofstream file(LOG_FILE, std::ios::app);

    if (!file.is_open()) {
        std::cerr << "Error: Unable to open the file!" << std::endl;
        exit(1);
    }

    for (const auto& ele : records) {
        file << ele << "\n";
    }

    file.close();
    std::cout << records.size() << " new lines added to csv!" << std::endl;
    records.clear();
}

class VsockStream {
private:
    int conn_tmo;
    int sock;

public:
    std::vector<double> records;
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
        records.push_back(delta / 1000.0);  // convert nano to micro
    }

    void disconnect() {
        close(sock);
        // assert(records.size() % 2);
        auto new_records = records;
        std::sort(new_records.begin(), new_records.end());

        std::cout << "For " << new_records.size() << " samples, median = " << new_records[new_records.size() / 2] << "\u00B5s" << std::endl;
        double mean = std::accumulate(new_records.begin(), new_records.end(), 0.0) / new_records.size();
        double res = std::accumulate(new_records.begin(), new_records.end(), 0.0, [mean](double acc, double val) {
            return acc + (val - mean) * (val - mean);
        }) / new_records.size();
        std::cout << "90th: " << new_records[static_cast<size_t>(0.9 * new_records.size())] << "\u00B5s"<< std::endl;
        std::cout << "95th: " << new_records[static_cast<size_t>(0.95 * new_records.size())] << "\u00B5s"<< std::endl;
        std::cout << "99th: " << new_records[static_cast<size_t>(0.99 * new_records.size())] << "\u00B5s"<< std::endl;
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

    int64_t start_time = std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
    int64_t count = 0;

    while(true) {
        count++;
        uint64_t time_now = std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
        client.send_data(&time_now, sizeof(time_now));
        if (count >= 10000) {
            count == 0;
            if (EXPERIMENT_TIME <= ((time_now - start_time) / 1'000'000'000) / 60) {
                break;
            }
        }
    }

    int64_t end_time = std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
    std::cout << "Msg rate: " << client.records.size() / ((end_time-start_time)/1'000'000'000) << std::endl;

    client.disconnect();
    log_and_clear(client.records);
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
