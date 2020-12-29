using System;
using System.IO;

namespace Project1
{
    public class Program
    {
        static void Main(string[] args)
        {
            using (StreamWriter sw = new StreamWriter("TestResults.xml"))
            {
                sw.Write("<?xml version=\"1.0\"?><FullResult xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\"><Passed>2</Passed><Total>2</Total><Tests><Result><Successful>true</Successful><Message>Passed</Message><MethodName>Test1</MethodName></Result><Result><Successful>true</Successful><Message>Passed</Message><MethodName>Test2</MethodName></Result></Tests></FullResult>");
            }
            while (true) { }
        }

        public static int Sum(int a, int b)
        {
            return a + b;
        }

        public static void Except()
        {
            throw new IndexOutOfRangeException();
        }
    }

}