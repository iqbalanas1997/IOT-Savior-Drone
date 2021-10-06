import React, {useState} from 'react'

function MissionSetup() {

          // state of user input drop height
          const [dropHeight, setDropHeight] = useState('')
          // state of user input drop columns
          const [dropColumns, setDropColumns] = useState('')
          // state of user input drop rows
          const [dropRows, setDropRows] = useState('')
          // state of user input drop spacing
          const [dropSpacing, setDropSpacing] = useState('')
          
          // Submit Flight Parameters to Backend
          function submitParams() {
            // create an object of flight parameters from user submitted values
            const flightParams = ({
              dropHeight: dropHeight,
              dropColumns: dropColumns,
              dropRows: dropRows,
              dropSpacing: dropSpacing
            })
            // if all user inputs are filled in
            if (dropHeight !== '' && dropColumns !== '' && dropRows !== '' && dropSpacing !== '') {
              // send JSON object of flight parameters to backend with POST method
              fetch('/api/params', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(flightParams)
              }).then(res => console.log(res.ok))
              .then(() => setFlightStarted(true))
              .then(() => {
                socket.emit('flight-start')
                socket.emit('flight-stats')
            })
              .catch(err => console.log(err))
            } else {
              console.log('Specify all parameters')
            }
            }

    return (
        <>
        <div className='md:grid md:grid-cols-2 items-center max-w-5xl mx-auto'>
          {/* Image showing example mission route */}
          <div className='m-auto container max-w-lg'>
            <img src={Route} alt='Example mission route'/>
          </div>
          {/* Input boxes for flight parameters */}
          <div>
            <h2 className='text-3xl lg:text-4xl text-blue-500'>Mission Parameters</h2>
            <form className='my-3 flex flex-col place-items-center text-2xl'>
              <Input name='Height' onChange={e => setDropHeight(e.target.value)} value={dropHeight}/>
              <Input name='Columns' onChange={e => setDropColumns(e.target.value)} value={dropColumns}/>
              <Input name='Rows' onChange={e => setDropRows(e.target.value)} value={dropRows}/>
              <Input name='Spacing' onChange={e => setDropSpacing(e.target.value)} value={dropSpacing}/>
            </form>
          </div>

        </div>

        <div className='mt-6'>
            <button 
              className='text-xl md:text-2xl py-2 px-4 mb-8 border-2 rounded-lg border-green-600 hover:bg-green-600 hover:text-white' 
              onClick={submitParams}>
                Start Flight
            </button>
          </div>

        </>
    )
}

export default MissionSetup
