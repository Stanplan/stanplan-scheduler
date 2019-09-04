var fs = require('fs');
var path = require('path');
var { PythonShell } = require('python-shell');

function runScheduler(classesAndPrefsJson) {
  fs.writeFileSync(path.resolve('.') + '/Data/input.json', JSON.stringify(classesAndPrefsJson));

  // Runs scheduler in a Python shell
  // ----------------------------------
  let options = {
    pythonOptions: ['-u'], // get print results in real-time
    pythonPath: 'python3',
    scriptPath: path.resolve('.') + '/Data',
    args: ['-userInput', 'input.json']
  };

  PythonShell.run('run_sched.py', options, function (err, results) {
    if (err) throw err;
    //console.log("Results: " + results);
    console.log("Successfully created four-year schedule");

    delete require.cache[require.resolve('./Data/output.json')];
    let fourYearPlan = require('./Data/output.json');
    res.status(200).json({ plan: fourYearPlan });
  });
}

module.exports = { runScheduler };
