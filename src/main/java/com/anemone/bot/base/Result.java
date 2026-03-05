package com.anemone.bot.base;

import java.util.function.Function;

/**
 * 操作结果封装 - 替代异常的错误处理方式
 * 
 * 封装操作成功/失败状态和返回值，使错误处理显式化。
 * 模仿 Rust 的 Result 类型和 Python 版本的 Result 类。
 * 
 * @param <T> 成功时返回的数据类型
 * 
 * Example:
 * <pre>{@code
 * Result<String> result = someOperation();
 * if (result.isSuccess()) {
 *     System.out.println(result.getValue());
 * } else {
 *     System.out.println("Error: " + result.getError());
 * }
 * }</pre>
 */
public class Result<T> {
    
    private final T value;
    private final String error;
    
    private Result(T value, String error) {
        this.value = value;
        this.error = error;
    }
    
    /**
     * 创建成功结果
     * 
     * @param value 成功值
     * @return 成功的 Result
     */
    public static <T> Result<T> ok(T value) {
        return new Result<>(value, null);
    }
    
    /**
     * 创建失败结果
     * 
     * @param error 错误信息
     * @return 失败的 Result
     */
    public static <T> Result<T> err(String error) {
        return new Result<>(null, error);
    }
    
    /**
     * 操作是否成功
     */
    public boolean isSuccess() {
        return error == null;
    }
    
    /**
     * 操作是否失败
     */
    public boolean isFailure() {
        return error != null;
    }
    
    /**
     * 获取成功值
     * 
     * @throws IllegalStateException 如果结果是失败的
     */
    public T getValue() {
        if (isFailure()) {
            throw new IllegalStateException("Cannot get value from failed result: " + error);
        }
        return value;
    }
    
    /**
     * 获取错误信息
     * 
     * @throws IllegalStateException 如果结果是成功的
     */
    public String getError() {
        if (isSuccess()) {
            throw new IllegalStateException("Cannot get error from successful result");
        }
        return error;
    }
    
    /**
     * 解包值，失败时返回默认值
     * 
     * @param defaultValue 默认值
     * @return 成功值或默认值
     */
    public T unwrapOr(T defaultValue) {
        return isSuccess() ? value : defaultValue;
    }
    
    /**
     * 映射成功值
     * 
     * @param mapper 映射函数
     * @return 映射后的 Result
     */
    public <R> Result<R> map(Function<T, R> mapper) {
        if (isSuccess()) {
            return Result.ok(mapper.apply(value));
        }
        return Result.err(error);
    }
    
    /**
     * 失败时映射错误信息
     * 
     * @param mapper 错误映射函数
     * @return 映射后的 Result
     */
    public Result<T> mapErr(Function<String, String> mapper) {
        if (isFailure()) {
            return Result.err(mapper.apply(error));
        }
        return this;
    }
    
    /**
     * 条件检查，快速创建 Result
     * 
     * @param condition 检查条件
     * @param error 条件为假时的错误信息
     * @param value 条件为真时的返回值
     * @return 根据条件返回 ok 或 err
     */
    public static <T> Result<T> check(boolean condition, String error, T value) {
        return condition ? ok(value) : err(error);
    }
}
