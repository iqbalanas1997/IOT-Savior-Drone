import React from 'react'
import { useContext } from 'react'
import AppContext from '../page-context'


function Button({ emit, className, children}) {
    
    const { socket, setPage } = useContext( AppContext )

    return (
            <div className={'my-4'}>
                <button
                className={'border-2 px-4 py-1 rounded-xl ' + className}
                onClick={() => {
                socket.emit(emit)
                setPage('log')
                }} >
                 {children}
                </button>
            </div>
    )
}

export default Button

