#include "Force.h"
#include <fstream>
#include <iostream>
int main()
{
    ForceSensor Ft("192.168.1.11");
    Ft.InitFTResponse();
    while(true)
    {
        std::vector<double> output;
        output = Ft.PYRead(1);
        // std::cout<<""<<Ft.PYRead(1)[0]<<std::endl;
    }
}
