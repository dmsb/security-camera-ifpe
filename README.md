# Olá, me chamo Diogo Muniz! 

O projeto security-camera-ifpe tem como objetivo ser um sistema web capaz de centralizar o monitoramento por câmeras IP de um estabelecimento
através de uma mesma rede wi-fi.

Este documento vem a descrever como realizar as configurações básicas no servidor para a execução do código.

Etapas necessárias:

1. Necessário ter instalado o MongoDB;
  1.1. Realizar a criação de um novo banco de dados no MongoDB;
  1.2. Realizar a criação de dois documentos no banco de dados criado: User e Camera;
  1.3. Através do arquivo .ini do projeto é necessário informar o endereço de acesso do banco de dados criado do MongoDB nas propriedades 
  [DEV][DB_URI] e [PRD][DB_URI].
  1.4 Realizar a inclusão de todos os usuários e cameras que o sistema consumirá do banco. Todos os campos dos objetos User e Camera estão descritos 
  no arquivo dataload/mongo/user.json e dataload/mongo/camera.json.

2. Criar uma conta de serviço Google (Google Service Account)
  2.1. Inserir o endereço da conta de serviço no arquivo .ini na propriedade: [GENERAL][GOOGLE_DRIVE_SERVICE_ACCOUNT_EMAIL];
  2.2. Para acesso pelo diretamente pelo drive dos arquivos transferidos para conta de serviço, é necessário criar uma pasta numa conta tradicional Gmail
  e compartilha-lá com a conta de serviço criada. Será a partir desta pasta que será manipulado tudo que a conta de serviço fará a partir desta aplicaçao.
  2.3. Inserir o ID da pasta compartilhada na propriedade [GENERAL][GOOGLE_DRIVE_SECURITY_CAMERA_VIDEO_FOLDER_ID] no arquivo .ini.

3. No arquivo .ini realizar as seguintes inclusões:
  3.1. Inserir as propriedades [GENERAL][SERVER_EMAIL_PASSWORD] e [GENERAL][SERVER_EMAIL_ADDRESS] para ser a conta remetente utilizada para 
  o envio de e-mails de redefinição de senha;
  3.2 Inserir a propriedade [GENERAL][SALT], para definir o sal utilizado na criptografia da senha dos usuários;
  3.3 Inserir a propriedade [GENERAL][RELATIVE_LOCAL_STORAGE_VIDEO_CAMERAS], para informar a pasta local do servidor que será armazenado temporariamente
  os vídeos antes de transferí-los para o Google Drive da conta de serviço da Google;
  3.4 Inserir a propriedade [DEV][LOG_FILE_NAME] e [PRD][LOG_FILE_NAME], para definir onde se localizará os arquivos de log do sistema, seja de produção
  ou de desenvolvimento.

4. Antes de executar o sistema python é preciso:
  4.1 Instalar o Python a partir da versão 3;
  4.2 Instalar todas as dependências do projeto, informadas no arquivo requirements.txt. (Executar o comando: pip install requirements.txt)

5. Caso o servidor esteja rodando num sistema Unix, pode ser necessário baixar e colocar o arquivo para habilitar a compressão de arquivos utilizando a
extensão h264. Para Windows, o software atualmente já está sendo utilizado o openh264-1.8.0-win64.dll.

6. Para executar o projeto em modo desenvolvimento, basta executar o arquivo app.py, nesta execução será executado um script para criação de registros
no banco de dados mongoDB para testes de desenvolvimento utilizando os arquivos dataload/mongo/user.json e dataload/mongo/camera.json. 
(Definir endereço de host)

7. Para executar o projeto em modo produção, basta executar o arquivo appWaitress.py. (Definir endereço de host)
  

 
