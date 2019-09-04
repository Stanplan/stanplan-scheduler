let { PythonShell } = require('python-shell');

let options = {
  pythonPath: 'python3',
  scriptPath: '.'
};

PythonShell.run('run_sched.py', options, function (err) {
  if (err) throw err;
  console.log("Completed!");
});
