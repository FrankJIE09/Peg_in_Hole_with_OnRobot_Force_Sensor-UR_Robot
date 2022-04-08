#include "Force.h"
#include <algorithm>
#include <iostream>
#include <fstream>
#include <iomanip>

void ForceSensor::MySleep(unsigned long ms)
{
    usleep(ms * 1000);
}

int ForceSensor::GetSequence() const
{
    return sequence_;
}

void ForceSensor::InitFTResponse()
{
    if (SocketConnect() != 0)
    {
        fprintf(stderr, "Could not connect to device...\r\n");
        return;
    }
    else
    {
//        fprintf(stdout, "Connected to Ethernet DAQ\r\n");
//        fflush(stdout);
    }

    if (GetCalibrationInfo() != 0)
    {
        fprintf(stderr, "Could not read calibration info...\r\n");
        return;
    }

    ftResponseStack_.clear();
    FTResponse localftResponse;

    for (int i = 0; i < INIT_SAMPLE_COUNT; ++i)
    {
        int readSuccess = ReadFT(&localftResponse);

        if (readSuccess == 0)
        {
            AccumulateReadings(&localftResponse);
        }
        else
        {
            fprintf(stderr, "Could not read F/T data, error code: %d\r\n", readSuccess);
            break;
        }
    }

    for (auto &t : initftResponse_)
    {
        t = .0;
    }

    for (std::size_t i{}; i < ftResponseStack_.size(); i++)
    {
        for (std::size_t j{}; j < 6; j++)
        {
            initftResponse_.at(j) += ftResponseStack_.at(i).at(j) / ftResponseStack_.size();
        }
    }

    for (auto &t : initftResponse_)
    {
        std::cout << t << std::endl;
    }

    SocketClose();
}

void ForceSensor::Read(int times)
{

    if (SocketConnect() != 0)
    {
        fprintf(stderr, "Could not connect to device...\r\n");
        return;
    }
    else
    {
//        fprintf(stdout, "Connected to Ethernet DAQ\r\n");
//        fflush(stdout);
    }

    ftResponseStack_.clear();
    FTResponse localftResponse;

    for (int i = 0; i < times; ++i)
    {
        int readSuccess = ReadFT(&localftResponse);

        if (readSuccess == 0)
        {
            AccumulateReadings(&localftResponse);
        }
        else
        {
            fprintf(stderr, "Could not read F/T data, error code: %d\r\n", readSuccess);
            break;
        }
    }

    for (auto &t : outputftResponse_)
    {
        t = .0;
    }

    for (std::size_t i{}; i < ftResponseStack_.size(); i++)
    {
        for (std::size_t j{}; j < 6; j++)
        {
            outputftResponse_.at(j) += ftResponseStack_.at(i).at(j) / ftResponseStack_.size();
        }
    }

    // for (auto &t : outputftResponse_)
    // {
    //     std::cout << t << std::endl;
    // }

//    fprintf(stdout, "Successfully read data from the FT sensor!\r\n");

    SocketClose();
}

void ForceSensor::SmoothReadings(int times)
{
}

int ForceSensor::SocketConnect()
{
    struct sockaddr_in addr;
    struct hostent *he;
    int err;

    socketHandle_ = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);

    if (socketHandle_ == -1)
    {
        fprintf(stderr, "Socket could not be opened.\n");
        return -2;
    }

    he = gethostbyname(ip_.c_str());
    memcpy(&addr.sin_addr, he->h_addr_list[0], he->h_length);
    addr.sin_family = AF_INET;
    addr.sin_port = htons(DAQ_PORT);
//    fprintf(stdout, "Connecting to Ethernet DAQ\r\n");
//    fflush(stdout);

    err = connect(socketHandle_, (struct sockaddr *)&addr, sizeof(addr));

    if (err < 0)
    {
        return -3;
    }
    return 0;
}

void ForceSensor::SocketClose()
{
    close(socketHandle_);
}

int ForceSensor::GetCalibrationInfo()
{
    int i;
    int sendSuccess;
    int readSuccess;
    ReadCalibrationCommand readCommand = {0};
    readCommand.command = READCALIBRATIONINFO;
    sendSuccess = send(socketHandle_, (const char *)&readCommand, sizeof(ReadCalibrationCommand), 0);
    if (sendSuccess < 0)
    {
        return sendSuccess;
    }

    readSuccess = recv(socketHandle_, (char *)&calibrationResponse_, sizeof(CalibrationResponse), 0);
    if (readSuccess < 0)
    {
        return readSuccess;
    }
    calibrationResponse_.header = htons(calibrationResponse_.header);
    calibrationResponse_.countsPerForce = ntohl(calibrationResponse_.countsPerForce);
    calibrationResponse_.countsPerTorque = ntohl(calibrationResponse_.countsPerTorque);

    for (i = 0; i < 6; ++i)
    {
        calibrationResponse_.scaleFactors[i] = htons(calibrationResponse_.scaleFactors[i]);
    }

    if (calibrationResponse_.header != 0x1234)
    {
        return -1;
    }
    return 0;
}

void ForceSensor::WriteLogs(const char *FileName)
{

    std::ofstream out;

    if (sequence_)
    {
        out.open(FileName, std::ios::app);
    }
    else
    {
        out.open(FileName, std::ios::ate);
    }

    out << sequence_ << ",";
    for (std::size_t i{}; i < 5; i++)
    {
        out << std::setprecision(4) << outputftResponse_.at(i) << ",";
    }

    out << std::setprecision(4) << outputftResponse_.at(5) << std::endl;

    out.close();

    sequence_++;
}

ForceSensor::int16 ForceSensor::swap_int16(int16 val)
{
    return (val << 8) | ((val >> 8) & 0xFF);
}

void ForceSensor::SwapFTResponseBytes(FTResponse *r)
{
    r->header = htons(r->header);
    r->status = htons(r->status);
    r->ForceX = swap_int16(r->ForceX);
    r->ForceY = swap_int16(r->ForceY);
    r->ForceZ = swap_int16(r->ForceZ);
    r->TorqueX = swap_int16(r->TorqueX);
    r->TorqueY = swap_int16(r->TorqueY);
    r->TorqueZ = swap_int16(r->TorqueZ);
}

int ForceSensor::ReadFT(FTResponse *r)
{
    FTReadCommand readCommand = {0};
    int readSuccess;
    int sendSuccess;
    readCommand.command = READFT;
    sendSuccess = send(socketHandle_, (char *)&readCommand, sizeof(FTReadCommand), 0);

    if (sendSuccess < 0)
    {
        return sendSuccess;
    }

    readSuccess = recv(socketHandle_, (char *)r, sizeof(FTResponse), 0);

    if (readSuccess != sizeof(FTResponse))
    {
        return 1;
    }

    SwapFTResponseBytes(r);

    if (r->header != 0x1234)
    {
        return 2;
    }

    return 0;
}

void ForceSensor::AccumulateReadings(FTResponse *r)
{
    //! Code Below will be excuted only when readSuccess = 0
    double Fx = (double)r->ForceX / (double)calibrationResponse_.countsPerForce * (double)calibrationResponse_.scaleFactors[0];
    double Fy = (double)r->ForceY / (double)calibrationResponse_.countsPerForce * (double)calibrationResponse_.scaleFactors[1];
    double Fz = (double)r->ForceZ / (double)calibrationResponse_.countsPerForce * (double)calibrationResponse_.scaleFactors[2];
    double Tx = (double)r->TorqueX / (double)calibrationResponse_.countsPerTorque * (double)calibrationResponse_.scaleFactors[3];
    double Ty = (double)r->TorqueY / (double)calibrationResponse_.countsPerTorque * (double)calibrationResponse_.scaleFactors[4];
    double Tz = (double)r->TorqueZ / (double)calibrationResponse_.countsPerTorque * (double)calibrationResponse_.scaleFactors[5];

    std::array<double, 6> ReadingOnece{Fx, Fy, Fz, Tx, Ty, Tz};
    ReadingOnece.at(0) -= initftResponse_.at(0);
    ReadingOnece.at(1) -= initftResponse_.at(1);
    ReadingOnece.at(2) -= initftResponse_.at(2);
    ReadingOnece.at(3) -= initftResponse_.at(3);
    ReadingOnece.at(4) -= initftResponse_.at(4);
    ReadingOnece.at(5) -= initftResponse_.at(5);

    ftResponseStack_.push_back(ReadingOnece);
}

std::vector<double> ForceSensor::PYRead(int times)
{
    for (auto &t : outputftResponse_)
    {
        t = .0;
    }
    Read(times);
    std::vector<double> output;

    for (auto t : outputftResponse_)
    {
        output.push_back(t);
    }

    return output;
}
