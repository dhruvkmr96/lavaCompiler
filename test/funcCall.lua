class x
begin
    declare::int f(int x);
    function::void main()
    begin
        int x = f(5);
        print(x);
        return;
    end

    function:: int f(int x)
    begin
        if(x==0 or x==1)then return 1; end
        return f(x-1) + f(x-2);
    end
end
