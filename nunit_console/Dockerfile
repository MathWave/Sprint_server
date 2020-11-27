FROM mcr.microsoft.com/dotnet/core/sdk:3.1
RUN mkdir app
WORKDIR app
COPY . app
CMD ["dotnet", "exec", "--runtimeconfig", "config.json", "SprintTestEngine.exe", "{}.dll", "{}"]