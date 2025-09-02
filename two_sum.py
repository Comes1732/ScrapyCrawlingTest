
def bruteforce(nums, target):
    """
   暴力解法：双重循环检查所有组合
    """
    for i in range(len(nums) - 1):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []


def hashmap(nums, target):
    """哈希表优化解法：空间换时间（AI生成）
    
    Args:
        nums: 整数列表
        target: 目标值
        
    Returns:
        两个数的索引列表
    """
    num_map = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in num_map:
            return [num_map[complement], i]
        num_map[num] = i
    return []


def optimized(nums, target):
    """表达式优化解法：使用生成器表达式（AI生成）
    Args:
        nums: 整数列表
        target: 目标值
        
    Returns:
        两个数的索引列表
    """
    return next(
        (i, j) 
        for i in range(len(nums)) 
        for j in range(i + 1, len(nums)) 
        if nums[i] + nums[j] == target
    )


if __name__ == "__main__":
    # 测试用例
    test_nums = [2, 7, 11, 15]
    test_target = 9
    
    print("暴力解法结果:", bruteforce(test_nums, test_target))
    print("哈希表解法结果:", hashmap(test_nums, test_target))
    print("优化解法结果:",optimized(test_nums, test_target))
