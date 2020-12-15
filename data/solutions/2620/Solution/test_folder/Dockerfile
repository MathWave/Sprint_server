FROM mcr.microsoft.com/dotnet/core/sdk:3.1
RUN mkdir -p /app/
WORKDIR /app/
COPY . /app/
CMD dotnet exec --runtimeconfig SprintTestConsole.runtimeconfig.json SprintTestEngine.exe tests.dll