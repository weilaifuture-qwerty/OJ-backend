# Creating A+B Problem - Complete Guide

## Quick Setup (Using Management Command)

```bash
cd /Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge
python manage.py create_ab_problem
```

## Manual Setup (Using Script)

```bash
python create_ab_problem.py
```

## What the A+B Problem Includes

1. **Problem Details:**
   - Title: A+B Problem
   - ID: 1
   - Difficulty: Low
   - Time Limit: 1000ms (1 second)
   - Memory Limit: 256MB

2. **Description:**
   - Calculate the sum of two integers A and B
   - Input: Two integers separated by space
   - Output: The sum of A and B
   - Constraints: -10^9 ≤ A, B ≤ 10^9

3. **Test Cases (10 total):**
   - Basic cases: 1+2=3, 10+20=30
   - Edge cases: 0+0=0, negative numbers, large numbers

4. **Sample Solutions:**
   - Python: `a, b = map(int, input().split()); print(a + b)`
   - C++: Basic iostream solution
   - Java: Scanner-based solution

## Testing the Problem

### 1. Via Web Interface

1. Start the server:
   ```bash
   python manage.py runserver
   ```

2. Login as admin:
   - Username: root
   - Password: rootroot

3. Navigate to Problems section

4. Click on "A+B Problem"

5. Submit a solution:
   ```python
   a, b = map(int, input().split())
   print(a + b)
   ```

### 2. Via API

```bash
# Get problem details
curl http://localhost:8000/api/problem?problem_id=1

# Submit solution (requires authentication)
curl -X POST http://localhost:8000/api/submission/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -d '{
    "problem_id": "1",
    "language": "Python3",
    "code": "a, b = map(int, input().split())\\nprint(a + b)"
  }'
```

### 3. Testing with Different Languages

**Python 3:**
```python
a, b = map(int, input().split())
print(a + b)
```

**C++:**
```cpp
#include <iostream>
using namespace std;

int main() {
    int a, b;
    cin >> a >> b;
    cout << a + b << endl;
    return 0;
}
```

**Java:**
```java
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int a = sc.nextInt();
        int b = sc.nextInt();
        System.out.println(a + b);
    }
}
```

**JavaScript (Node.js):**
```javascript
const readline = require('readline');
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

rl.on('line', (line) => {
    const [a, b] = line.split(' ').map(Number);
    console.log(a + b);
    rl.close();
});
```

## Verifying Test Cases

The test cases are stored in:
```
data/test_case/ab_problem_test/
├── 1.in    (1 2)
├── 1.out   (3)
├── 2.in    (10 20)
├── 2.out   (30)
... (8 more test cases)
```

## Troubleshooting

### Problem Not Visible
- Check if `visible=True` in problem settings
- Ensure you're logged in
- Clear browser cache

### Submission Stays Pending
- Check if judge server is running
- Verify test cases exist in the correct directory
- Check Redis is running
- Look at Django logs for errors

### Wrong Answer Results
- Verify output format (should end with newline)
- Check for extra spaces or characters
- Test locally with the exact input/output

### Test Cases Not Found
- Ensure `data/test_case/ab_problem_test/` directory exists
- Check file permissions
- Verify test case files have correct names (1.in, 1.out, etc.)

## Adding More Test Cases

1. Edit the test cases in the script
2. Re-run the creation script
3. Or manually add files to `data/test_case/ab_problem_test/`

## Next Steps

1. Create more problems with varying difficulty
2. Add problems with multiple test cases
3. Create problems requiring special judge
4. Import problems from other platforms
5. Create contest with multiple problems