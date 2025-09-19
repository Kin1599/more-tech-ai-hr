import React, { useState, useRef, useEffect } from 'react';

export const CodeNotebookPanel = ({ panelHeight }) => {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('javascript');
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const textareaRef = useRef(null);

  const languages = [
    { value: 'javascript', label: 'JavaScript' },
    { value: 'python', label: 'Python' },
    { value: 'java', label: 'Java' },
    { value: 'cpp', label: 'C++' },
    { value: 'csharp', label: 'C#' },
    { value: 'go', label: 'Go' },
    { value: 'rust', label: 'Rust' },
    { value: 'typescript', label: 'TypeScript' }
  ];

  useEffect(() => {
    // Автоматическое изменение размера textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${panelHeight - 120}px`;
    }
  }, [panelHeight]);

  const runCode = async () => {
    if (!code.trim()) {
      setOutput('Введите код для выполнения');
      return;
    }

    setIsRunning(true);
    setOutput('Выполнение...');

    try {
      // Для демонстрации - простой интерпретатор JavaScript
      if (language === 'javascript') {
        // Создаем безопасную среду выполнения
        const originalConsole = console.log;
        let outputText = '';
        
        // Перехватываем console.log
        console.log = (...args) => {
          outputText += args.map(arg => 
            typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
          ).join(' ') + '\n';
        };

        try {
          // Выполняем код в безопасной среде
          const result = eval(code);
          if (result !== undefined) {
            outputText += String(result);
          }
        } catch (error) {
          outputText = `Ошибка: ${error.message}`;
        }

        // Восстанавливаем оригинальный console.log
        console.log = originalConsole;
        setOutput(outputText || 'Код выполнен без вывода');
      } else {
        setOutput(`Выполнение ${language} кода не поддерживается в демо-версии.\nИспользуйте JavaScript для тестирования.`);
      }
    } catch (error) {
      setOutput(`Ошибка выполнения: ${error.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const clearCode = () => {
    setCode('');
    setOutput('');
  };

  const downloadCode = () => {
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `code.${language === 'javascript' ? 'js' : language}`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const loadSampleCode = () => {
    const samples = {
      javascript: `// Пример алгоритма сортировки пузырьком
function bubbleSort(arr) {
  const n = arr.length;
  for (let i = 0; i < n - 1; i++) {
    for (let j = 0; j < n - i - 1; j++) {
      if (arr[j] > arr[j + 1]) {
        [arr[j], arr[j + 1]] = [arr[j + 1], arr[j]];
      }
    }
  }
  return arr;
}

const numbers = [64, 34, 25, 12, 22, 11, 90];
console.log("Исходный массив:", numbers);
console.log("Отсортированный массив:", bubbleSort([...numbers]));`,
      python: `# Пример алгоритма быстрой сортировки
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

numbers = [64, 34, 25, 12, 22, 11, 90]
print("Исходный массив:", numbers)
print("Отсортированный массив:", quick_sort(numbers))`,
      java: `// Пример алгоритма бинарного поиска
public class BinarySearch {
    public static int binarySearch(int[] arr, int target) {
        int left = 0, right = arr.length - 1;
        while (left <= right) {
            int mid = left + (right - left) / 2;
            if (arr[mid] == target) return mid;
            if (arr[mid] < target) left = mid + 1;
            else right = mid - 1;
        }
        return -1;
    }
    
    public static void main(String[] args) {
        int[] arr = {1, 3, 5, 7, 9, 11, 13};
        int target = 7;
        int result = binarySearch(arr, target);
        System.out.println("Индекс элемента " + target + ": " + result);
    }
}`
    };
    
    setCode(samples[language] || '');
  };

  return (
    <div className="h-full flex flex-col bg-gray-750">
      {/* Панель инструментов */}
      <div className="flex items-center justify-between p-3 border-b border-gray-600">
        <div className="flex items-center space-x-3">
          {/* Выбор языка */}
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="px-2 py-1 bg-gray-700 text-white rounded text-sm"
          >
            {languages.map((lang) => (
              <option key={lang.value} value={lang.value}>
                {lang.label}
              </option>
            ))}
          </select>
          
          {/* Кнопка загрузки примера */}
          <button
            onClick={loadSampleCode}
            className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
          >
            Пример
          </button>
        </div>
        
        {/* Кнопки действий */}
        <div className="flex space-x-2">
          <button
            onClick={runCode}
            disabled={isRunning}
            className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {isRunning ? 'Выполнение...' : 'Выполнить'}
          </button>
          <button
            onClick={clearCode}
            className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
          >
            Очистить
          </button>
          <button
            onClick={downloadCode}
            className="px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700"
          >
            Скачать
          </button>
        </div>
      </div>
      
      {/* Редактор кода */}
      <div className="flex-1 flex">
        <div className="flex-1 flex flex-col">
          <div className="flex items-center justify-between p-2 bg-gray-800">
            <span className="text-white text-sm font-medium">Код ({language})</span>
            <span className="text-gray-400 text-xs">
              {code.length} символов
            </span>
          </div>
          <textarea
            ref={textareaRef}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder={`Введите ваш ${language} код здесь...`}
            className="flex-1 w-full p-3 bg-gray-900 text-green-400 font-mono text-sm resize-none border-none outline-none"
            style={{ 
              fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
              lineHeight: '1.5'
            }}
          />
        </div>
        
        {/* Панель вывода */}
        <div className="w-1/2 flex flex-col border-l border-gray-600">
          <div className="flex items-center justify-between p-2 bg-gray-800">
            <span className="text-white text-sm font-medium">Вывод</span>
          </div>
          <pre className="flex-1 p-3 bg-gray-900 text-white text-sm overflow-auto whitespace-pre-wrap">
            {output || 'Вывод появится здесь после выполнения кода...'}
          </pre>
        </div>
      </div>
    </div>
  );
};
