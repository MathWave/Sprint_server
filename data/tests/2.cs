using NUnit.Framework;
using Calculator;
using System.IO;
using Darwin;
using System;

namespace TestProject2
{
    [TestFixture]
    public class Tests
    {
        [Test]
        public void Test1()
        {
            Assert.AreEqual(Calc.Sum(1, 1), 2);
        }

        [Test]
        public void Test2()
        {
            Assert.AreEqual(Calc.Sum(1, 1), 2);
        }
       
        [Test]
        public void Test3()
        {
DObject d = new DObject("Calculator.Calc");
Assert.AreEqual((int)d.InvokeMethod("A"), 6);
        }

    }
}



