from judge.code_executor import CodeExecutor

@login_required
def run_code(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            problem_id = data.get('problem_id')
            language = data.get('language')
            code = data.get('code')
            test_input = data.get('test_input')

            if not all([problem_id, language, code]):
                return JsonResponse({
                    'error': 'Missing required fields'
                }, status=400)

            try:
                problem = Problem.objects.get(_id=problem_id)
            except Problem.DoesNotExist:
                return JsonResponse({
                    'error': 'Problem not found'
                }, status=404)

            if language not in problem.languages:
                return JsonResponse({
                    'error': 'Language not supported for this problem'
                }, status=400)

            executor = CodeExecutor(
                language=language,
                code=code,
                input_data=test_input,
                time_limit=problem.time_limit,
                memory_limit=problem.memory_limit
            )

            result = executor.execute()
            return JsonResponse(result)

        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)

    return JsonResponse({
        'error': 'Method not allowed'
    }, status=405) 