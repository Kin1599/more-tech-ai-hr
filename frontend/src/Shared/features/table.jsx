import {Link} from 'react-router-dom';
import arrowIcon from '../imgs/arrow-right.svg';

const CustomTable = ({namesArr, data}) => {
  console.log(data);
  return (
    <div className='flex flex-col gap-[20px]'>
      <div className='flex justify-between items-center p-[20px] pb-0 pt-0 font-bold text-[24px]'>
        {namesArr.map((el) => (
          <div key={el.name} style={{width: el.width}} className='text-center truncate'>
            {el.name}
          </div>
        ))}
      </div>
      <div className='flex flex-col gap-[10px]'>
        {data.map((el, index) => (
          <Link
            key={el.vacancyId || index}
            to={`/vacancy/${el.vacancyId}`}
            className='flex justify-between items-center bg-white border border-solid border-[#303030] rounded-[20px] p-[20px] hover:bg-[#eb5e28] hover:text-white transition-colors duration-200 cursor-pointer group text-[20px]'
          >
            {el.map((elData, colIndex) => (
              <div key={elData.name} style={{width: elData.width}} className='text-center truncate'>
                {colIndex === el.length - 1 ? <div className='group-hover:hidden truncate'>{elData.name}</div> : null}
                {colIndex === el.length - 1 ? (
                  <div className='hidden group-hover:flex items-center gap-[10px]'>
                    Перейти <img src={arrowIcon} alt='Перейти' className='w-[30px] h-[30px]'></img>
                  </div>
                ) : (
                  elData.name
                )}
              </div>
            ))}
          </Link>
        ))}
      </div>
    </div>
  );
};

export default CustomTable;
