from paramiko import SSHClient, AutoAddPolicy


class ServerClient:
    HOST = '77.232.135.162'
    PORT = 57821

    
    def __init__(self, user: str, password: str) -> None:
        self._username = user
        self._user_password = password
        
        ssh_client = SSHClient()
        ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    
        ssh_client.connect(
            hostname=self.HOST,
            port=self.PORT,
            username=self._username,
            password=self._user_password
        )
        
        self._client = ssh_client.open_sftp()
    
    def download_file(self, file_path: str, path_to_save: str):
        self._client.get(remotepath=file_path, localpath=path_to_save)

    def upload_file(self, file_path: str, path_to_save: str):
        self._client.put(localpath=file_path, remotepath=path_to_save)
