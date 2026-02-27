const { BrowserWindow, app } = require('electron');
const path = require('path');
const fs = require('fs');

// Detectar modo de desenvolvimento
const isDev = !app.isPackaged;

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      sandbox: true
    }
  });

  if (isDev) {
    // Em desenvolvimento, conectar ao servidor React
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    // Em produção, usar servidor HTTP interno
    const express = require('express');
    const http = require('http');
    
    const server = express();
    const buildPath = path.join(__dirname, '../build');
    
    console.log('📁 Build path:', buildPath);
    console.log('📄 Build exists:', fs.existsSync(buildPath));
    
    // Servir arquivos estáticos
    server.use(express.static(buildPath));
    
    // Rota catch-all para SPA
    server.use((req, res) => {
      res.sendFile(path.join(buildPath, 'index.html'));
    });

    const httpServer = http.createServer(server);
    httpServer.listen(0, 'localhost', () => {
      const port = httpServer.address().port;
      const url = `http://localhost:${port}`;
      console.log('🚀 Carregando app em:', url);
      mainWindow.loadURL(url);
    });
  }

  return mainWindow;
}

module.exports = { createWindow };
