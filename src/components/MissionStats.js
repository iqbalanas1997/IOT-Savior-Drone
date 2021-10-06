import { AiOutlineColumnHeight } from "react-icons/ai";
import { IoSpeedometer } from "react-icons/io5";
import { GiBattery100 } from "react-icons/gi";
import { FaArrowsAltH, FaArrowsAltV } from "react-icons/fa";
import { ImBlocked } from "react-icons/im";

export default function MissionStats({flightStats, row, col}) {
    
    return(
    <>
        <h2>Flight Stats</h2>
        <div className='grid grid-cols-2 grid-rows-6 mission-log md:text-2xl'>

            <div className='self-center flex flex-row justify-center items-center'>
               <GiBattery100 className='mx-2'/>
               Battery
            </div>
            <div className='self-center flex flex-row justify-center items-center'>
                {(flightStats.battery) ? (flightStats.battery + ' %') : 'N/A'}
            </div>

            <div className='self-center flex flex-row justify-center items-center'>
                <AiOutlineColumnHeight className='mx-2'/>
                Altitude
            </div>
            <div className='self-center flex flex-row justify-center items-center'>
                {flightStats.altitude?.toFixed(2) ?? 'N/A'}
            </div>

            <div className='self-center flex flex-row justify-center items-center'>
                <IoSpeedometer className='mx-2'/>
                Velocity
            </div>
            <div className='self-center flex flex-row justify-center items-center'>
                {flightStats.airspeed?.toFixed(2) ?? 'N/A'}
            </div>

            <div className='self-center flex flex-row justify-center items-center'>
                <FaArrowsAltH className='mx-2'/>
                Column
            </div>
            <div className='self-center flex flex-row justify-center items-center'>
                {col ?? 'N/A'}
            </div>

            <div className='self-center flex flex-row justify-center items-center'>
                <FaArrowsAltV className='mx-2'/>
                Row
            </div>
            <div className='self-center flex flex-row justify-center items-center'>
                {row ?? 'N/A'}
            </div>

            <div className='self-center flex flex-row justify-center items-center'>
                <ImBlocked className='mx-2'/>
                Obstacles
            </div>
            <div className='self-center flex flex-row justify-center items-center'>
                {flightStats.obstacle ?? 'None'}
            </div>

        </div>
    </>)
}