const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let pythonProcess = null;
const pythonPort = 8080; // Define a port for the Python backend

function createWindow () {
  // 创建浏览器窗口。
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false, // 仅开发环境可用
      webSecurity: false      // 仅开发环境可用
    }
  });

  // 加载 index.html
  mainWindow.loadURL('http://127.0.0.1:8080/');

  // 打开开发者工具。
  mainWindow.webContents.openDevTools();

  // Send the port number to the renderer process once it's ready
  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.webContents.send('set-python-port', pythonPort);
  });
}

// Electron会在初始化完成并且准备好创建浏览器窗口时调用这个方法
// 部分 API 在 ready 事件触发后才能使用。
app.whenReady().then(() => {
  // Start the Python backend
  console.log(`Starting Python backend on port ${pythonPort}...`);
  // Ensure 'flask' command is available or use the full path to the flask executable
  // Use 'flask run --port <port>' to start the development server
  pythonProcess = spawn('flask', ['run', '--port', pythonPort.toString()], {
    stdio: 'pipe',
    // Set the working directory to the app's directory if needed, though flask usually handles this
    // cwd: __dirname 
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python stdout: ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python stderr: ${data}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
    pythonProcess = null; // Reset process variable
  });

  pythonProcess.on('error', (err) => {
    console.error('Failed to start Python process:', err);
  });

  createWindow();

  app.on('activate', function () {
    // 在 macOS 上，当单击 dock 图标并且没有其他窗口打开时，
    // 通常在应用程序中重新创建一个窗口。
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

// 除了 macOS 外，当所有窗口都被关闭的时候退出程序。
// 因此，通常对应用程序和它们的菜单栏来说应该时刻保持激活状态，
// 直到用户使用 Cmd + Q 明确退出。
app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

// Kill Python process before quitting
app.on('will-quit', () => {
  if (pythonProcess) {
    console.log('Killing Python process...');
    pythonProcess.kill();
    pythonProcess = null;
  }
});

// 在这个文件中，你可以包含应用程序剩余的主进程代码。
// 也可以拆分成几个文件，然后用 require 导入。