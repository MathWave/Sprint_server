using System;
using System.Reflection;

namespace Darwin
{
    public class DObject
    {

        private object _thisObject;

        private BindingFlags AllFlags => BindingFlags.NonPublic | BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static;

        private MethodInfo GetMethodInfo(string methodName)
        {
            return _thisObject.GetType().GetMethod(methodName, AllFlags);
        }

        public DObject(string objectType)
        {
            foreach (Assembly ass in AppDomain.CurrentDomain.GetAssemblies())
            {
                try
                {
                    Type t = ass.GetType(objectType);
                    _thisObject = Activator.CreateInstance(t);
                    break;
                }
                catch (ArgumentNullException)
                {
                }
                catch (NullReferenceException)
                {
                }
            }
            if (_thisObject == null)
                throw new ArgumentException();
        }

        public object GetObject => _thisObject;

        public object this[string name]
        {
            get {
                var type = _thisObject.GetType();
                try
                {
                    return type.GetField(name, AllFlags).GetValue(_thisObject);
                }
                catch
                {
                    return type.GetProperty(name, AllFlags).GetValue(_thisObject);
                }
            }
            set {
                var type = _thisObject.GetType();
                try
                {
                    type.GetProperty(name, AllFlags).SetValue(_thisObject, value);
                }
                catch
                {
                    type.GetField(name, AllFlags).SetValue(_thisObject, value);
                }
            }
        }

        public object InvokeMethod(string methodName, object[] inputValues = null)
        {
            MethodInfo mi = GetMethodInfo(methodName);
            return mi.Invoke(_thisObject, inputValues);
        }

    }
}