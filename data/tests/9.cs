using System.IO;
using System;
using SprintTest;

namespace TestsProject
{
    public class Tests
    {
        StringReader sr;
        StringWriter sw;
        DObject prog;


        [SetUp]
        public void Setup()
        {
            sw = new StringWriter();
            sr = new StringReader("");
            Console.SetOut(sw);
            prog = new DObject("TaskA.Programm");
        }

        [Test]
        public void Test1()
        {
            string inFile = "01";
            string outFile = inFile + ".a";
            string expected = File.ReadAllText(outFile).Trim();
            sr = new StringReader(File.ReadAllText(inFile).Trim());
            Console.SetIn(sr);
            prog.InvokeMethod("Main", new object[] { new string[] { } });
            string result = sw.ToString().Trim();
            Assert.AreEqual(expected, result);
        }

        [Test]
        public void Test2()
        {
            string inFile = "02";
            string outFile = inFile + ".a";
            string expected = File.ReadAllText(outFile).Trim();
            sr = new StringReader(File.ReadAllText(inFile).Trim());
            Console.SetIn(sr);
            prog.InvokeMethod("Main", new object[] { new string[] { } });
            string result = sw.ToString().Trim();
            Assert.AreEqual(expected, result);
        }
    }
}




