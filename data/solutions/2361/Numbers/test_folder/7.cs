using NUnit.Framework;
using Darwin;
using System.IO;
using System;
using Numbers;
using System.Reflection;

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
            new Numbers.Program();
            sw = new StringWriter();
            sr = new StringReader("");
            Console.SetOut(sw);
            prog = new DObject("Numbers.Program");
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

        [Test]
        public void Test3()
        {
            string inFile = "03";
            string outFile = inFile + ".a";
            string expected = File.ReadAllText(outFile).Trim();
            sr = new StringReader(File.ReadAllText(inFile).Trim());
            Console.SetIn(sr);
            prog.InvokeMethod("Main", new object[] { new string[] { } });
            string result = sw.ToString().Trim();
            Assert.AreEqual(expected, result);
        }

        [Test]
        public void Test4()
        {
            string inFile = "04";
            string outFile = inFile + ".a";
            string expected = File.ReadAllText(outFile).Trim();
            sr = new StringReader(File.ReadAllText(inFile).Trim());
            Console.SetIn(sr);
            prog.InvokeMethod("Main", new object[] { new string[] { } });
            string result = sw.ToString().Trim();
            Assert.AreEqual(expected, result);
        }

        [Test]
        public void Test5()
        {
            string inFile = "05";
            string outFile = inFile + ".a";
            string expected = File.ReadAllText(outFile).Trim();
            sr = new StringReader(File.ReadAllText(inFile).Trim());
            Console.SetIn(sr);
            prog.InvokeMethod("Main", new object[] { new string[] { } });
            string result = sw.ToString().Trim();
            Assert.AreEqual(expected, result);
        }

        [Test]
        public void Test6()
        {
            string inFile = "06";
            string outFile = inFile + ".a";
            string expected = File.ReadAllText(outFile).Trim();
            sr = new StringReader(File.ReadAllText(inFile).Trim());
            Console.SetIn(sr);
            prog.InvokeMethod("Main", new object[] { new string[] { } });
            string result = sw.ToString().Trim();
            Assert.AreEqual(expected, result);
        }

        [Test]
        public void Test7()
        {
            string inFile = "07";
            string outFile = inFile + ".a";
            string expected = File.ReadAllText(outFile).Trim();
            sr = new StringReader(File.ReadAllText(inFile).Trim());
            Console.SetIn(sr);
            prog.InvokeMethod("Main", new object[] { new string[] { } });
            string result = sw.ToString().Trim();
            Assert.AreEqual(expected, result);
        }

        [Test]
        public void Test8()
        {
            string inFile = "08";
            string outFile = inFile + ".a";
            string expected = File.ReadAllText(outFile).Trim();
            sr = new StringReader(File.ReadAllText(inFile).Trim());
            Console.SetIn(sr);
            prog.InvokeMethod("Main", new object[] { new string[] { } });
            string result = sw.ToString().Trim();
            Assert.AreEqual(expected, result);
        }

        [Test]
        public void Test9()
        {
            string inFile = "09";
            string outFile = inFile + ".a";
            string expected = File.ReadAllText(outFile).Trim();
            sr = new StringReader(File.ReadAllText(inFile).Trim());
            Console.SetIn(sr);
            prog.InvokeMethod("Main", new object[] { new string[] { } });
            string result = sw.ToString().Trim();
            Assert.AreEqual(expected, result);
        }

        [Test]
        public void Test10()
        {
            string inFile = "10";
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
