import React from 'react'

function Camera() {
    return (
        <>
        <h2>Live Camera Feed</h2>

            <div>
                <img 
                className='mx-auto my-6'
                src='/stream/video.mjpeg'/>
            </div>
            
        </>
    )
}

export default Camera
