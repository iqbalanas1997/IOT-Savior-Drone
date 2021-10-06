const Input = ({name, onChange, value, unit}) => {

return(
<div className="container text-xl md:text-2xl max-w-xs grid grid-cols-2 gap-0 overflow-hidden my-3 px-6">
    <div>
        <label>{name}</label>
    </div>
    <div>
        <input className='border-2 rounded-lg max-w-lg w-20 focus:outline-none' onChange={onChange} value={value} type="number"/>
        <p className='inline ml-2'>{unit}</p>
    </div>
</div>
)
}
export default Input

