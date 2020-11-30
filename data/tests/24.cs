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
            string outfile = input + ".a";
            string expected = File.ReadAllText(outfile).Trim().Replace("\r", "");
            sr = new StringReader(File.ReadAllText(input).Trim().Replace("\r", ""));
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
            prog = new DObject("SampleProject.dll", "Program");
        }

        [Test]
        public void Test1()
        {
            TestInOut("001");
        }

        [Test]
        public void Test2()
        {
            TestInOut("002");
        }

        [Test]
        public void Test3()
        {
            TestInOut("003");
        }

        [Test]
        public void Test4()
        {
            TestInOut("004");
        }

        [Test]
        public void Test5()
        {
            TestInOut("005");
        }

        static void Main(string[] args)
        {
            Runner.Run("Tests");
        }
    }
}
