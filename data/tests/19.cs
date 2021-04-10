using System;
using SprintTest;
using System.IO;

namespace Tests
{
    class Program
    {
        StringReader sr;
        StringWriter sw;
        DObject prog;

        public void TestInOut(string input)
        {
            string expected = input + "\n" + input + "\n" + input;
            sr = new StringReader(input);
            sw = new StringWriter();
            Console.SetIn(sr);
            Console.SetOut(sw);
            prog.InvokeMethod("Main", new object[] { new string[] { } });
            string result = sw.ToString().Trim().Replace("\r", "");
            Assert.AreEqual(expected, result);
        }

        [SetUp]
        public void Setup()
        {
            prog = new DObject("SampleProject.dll", "Project1.Program");
        }

        [Test]
        public void Test1()
        {
            TestInOut("123");
        }

        [Test]
        public void Test2()
        {
            TestInOut("Hello!!!");
        }

        static void Main(string[] args)
        {
            Runner.Run("Tests");
        }
    }
}


