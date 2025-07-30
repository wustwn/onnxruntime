const fs = require('fs');
const { spawn } = require('child_process');
const path = require('path');

const deviceType = 'gpu';
const logoutFile = `./out/test-out-${deviceType}.log`;
const postProcessOutFile = logoutFile.replace('.log', '.json');
const pyScriptFile = './post-process-log.py';
const timeout = 30000; // 10 seconds

// Ensure the directory exists
const dir = path.dirname(logoutFile);

if (!fs.existsSync(dir)) {
  fs.mkdirSync(dir, { recursive: true });
}
const logFile = fs.createWriteStream(logoutFile, { flags: 'a' });

let timer;
function closeStreamIfNoData() {
  timer = setTimeout(() => {
    console.log(`No new data written for ${timeout / 1000} seconds. Closing the log file stream.`);
    logFile.end();

    // execute the pycmd to post process the logout
    const pyProcess = spawn('python', [pyScriptFile, logoutFile, postProcessOutFile], {
      shell: true, // Enable shell features like output redirection
    });

    pyProcess.stdout.on('data', (data) => {
      console.log(`stdout: ${data.toString()}`);
    });

    pyProcess.stderr.on('data', (data) => {
      console.log(`stderr: ${data.toString()}`);
    });

    pyProcess.on('close', (code) => {
      console.log(`Process exited with code: ${code}`);
      process.exit(code);
    });
  }, timeout);
}

// clear the logFile before writing
fs.writeFileSync(logoutFile, ''); // Clear the log file before writing

// Spawn the process
const child = spawn(
  'npm',
  [
    'run',
    'test',
    '--',
    'suite1',
    '-b=webnn',
    '--wasm-number-threads',
    '1',
    '-d',
    '--webnn-device-type',
    deviceType,
    '--chromium-flags=--use-redist-dml',
  ],
  {
    shell: true, // Enable shell features like output redirection
  },
);

// Handle stdout
child.stdout.on('data', (data) => {
  console.log(`stdout: ${data.toString()}`);
  logFile.write(data); // Write to log file
  clearTimeout(timer); // Clear the previous timer
  closeStreamIfNoData(); // Reset the timer
});

// Handle stderr
child.stderr.on('data', (data) => {
  console.error(`stderr: ${data.toString()}`);
  logFile.write(data); // Write to log file
  clearTimeout(timer); // Clear the previous timer
  closeStreamIfNoData(); // Reset the timer
});

// Handle process exit
child.on('close', (code) => {
  console.log(`Process exited with code: ${code}`);
  clearTimeout(timer); // Clear timeout on process exit
  logFile.end(); // Close the log file when done
});

// Handle process error
child.on('error', (err) => {
  console.error(`Failed to start process: ${err.message}`);
  clearTimeout(timer); // Clear timeout on error
  logFile.end(); // Close the log file on error
});

// Initialize the timer to check for inactivity
closeStreamIfNoData();
