#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include "Force.h"

// ----------------
// Python interface
// ----------------
namespace py = pybind11;

PYBIND11_MODULE(FTReading, m)
{
    py::class_<ForceSensor>(m, "FTReading")
        .def(py::init<char *>(), "Constructor with ip")
        .def("InitFT", &ForceSensor::InitFTResponse, "Init the Sensor Reading")
        .def("GetReading", &ForceSensor::PYRead, "Input Read times for smooth");
}
