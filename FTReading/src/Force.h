#ifndef CALIBRATION_FORCE_H
#define CALIBRATION_FORCE_H
#endif

#include <arpa/inet.h>
#include <sys/socket.h>
#include <netdb.h>
#include <unistd.h>
typedef int SOCKET_HANDLE;

#include <sys/types.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <string>
#include <array>
#include <vector>

//#pragma pack(1)

//#define PORT			49151	/* Port the Ethernet DAQ always uses */
//#define SAMPLE_COUNT	100		/* 100 incoming samples */

#define READFT 0
#define READCALIBRATIONINFO 1

//! \brief The ForceSensor class
//! Constructor: IP-Address
//!              File Name
class ForceSensor
{

    const int DAQ_PORT = 49151;
    const int INIT_SAMPLE_COUNT = 10000;

    typedef unsigned int uint32;
    typedef int int32;
    typedef unsigned short uint16;
    typedef short int16;
    typedef unsigned char byte;

    typedef struct FTResponseStruct
    {
        uint16 header;
        uint16 status;
        int16 ForceX;
        int16 ForceY;
        int16 ForceZ;
        int16 TorqueX;
        int16 TorqueY;
        int16 TorqueZ;

        FTResponseStruct() : header(0),
                             status(0),
                             ForceX(0),
                             ForceY(0),
                             ForceZ(0),
                             TorqueX(0),
                             TorqueY(0),
                             TorqueZ(0)
        {
        }
    } FTResponse;

    typedef struct CalibrationResponseStruct
    {
        uint16 header;
        byte forceUnits;
        byte torqueUnits;
        uint32 countsPerForce;
        uint32 countsPerTorque;
        uint16 scaleFactors[6];
    } CalibrationResponse;

    typedef struct FTReadCommandStruct
    {
        byte command;
        byte reserved[19];
    } FTReadCommand;

    typedef struct ReadCalibrationCommandStruct
    {
        byte command;
        byte reserved[19];
    } ReadCalibrationCommand;

public:
    ForceSensor(const char *ip_address) : ip_(ip_address),
                                          socketHandle_(),
                                          initftResponse_(),
                                          outputftResponse_(),
                                          ftResponseStack_(),
                                          sequence_(0),
                                          calibrationResponse_()
    {
    }

    ~ForceSensor() = default;

    //! \brief InitFTResponse
    //! Get Calibration Information
    void InitFTResponse();

    //! \brief Read Remote F/T Sensor some times and Take average
    //! \param times
    void Read(int times);

    //! \brief WriteLogs, Output Formata:    Sequence,FX,FY,FZ,TX,TY,TZ
    //! \param FileName
    void WriteLogs(const char *FileName = "../data/FT.txt");

    //! TODO
    void WriteJson();

    //! TODO
    void Plot();

    //! \brief MySleep  Sleep ms milliseconds
    //! \param ms
    void MySleep(unsigned long ms);

    //! \brief ShowCalibrationInfo
    void ShowCalibrationInfo();

    int GetSequence() const;

    //!
    //! \brief PYRead
    //! \param times
    //! \return FX,FY,FZ,TX,TY,TZ
    std::vector<double> PYRead(int times);

private:
    std::string ip_; // ip_address of remote sensor

    SOCKET_HANDLE socketHandle_; //Handle to UDP socket used to communicate with Ethernet DAQ.

    std::array<double, 6> initftResponse_;

    std::array<double, 6> outputftResponse_;

    std::vector<std::array<double, 6>> ftResponseStack_;

    int sequence_;

    CalibrationResponse calibrationResponse_; // class variable to hold calibration info datas

    int SocketConnect();

    void SocketClose();

    int GetCalibrationInfo();

    void SmoothReadings(int times);

    int ReadFT(FTResponse *r);

    void SwapFTResponseBytes(FTResponse *r);

    void AccumulateReadings(FTResponse *r);

    int16 swap_int16(int16 val);
};
