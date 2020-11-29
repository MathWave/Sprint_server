FROM mcr.microsoft.com/dotnet/core/sdk:3.1
RUN mkdir -p /usr/src/app/
WORKDIR /usr/src/app/
COPY . /usr/src/app/
CMD dotnet exec --runtimeconfig SprintTestConsole.runtimeconfig.json SprintTestEngine.exe tests.dll