# stanplan-scheduler

NOTE: All code is python3

Initial Setup:

` cd TestData
  python genTests.py
`

Hierarchy of the Scheduler Code:
` indirect_scheduler.py ` is the heart of the scheduler
` sched_utils.py ` has a handful of useful utils
` run_sched.py ` invokes the scheduler and loads the data

If you want to load a specific file or change the test case, you want to edit ` run_sched.py `

To run the scheduler use:
` python run_sched.py `

or to invoke with flags use:

` python run_sched.py -db_path Data/fullGoldDB.db -userInput TestData/test9.json -outputPath output.json  `
